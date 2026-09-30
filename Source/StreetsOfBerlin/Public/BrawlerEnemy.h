#pragma once

#include "CoreMinimal.h"
#include "BrawlerFighter.h"
#include "BrawlerEnemy.generated.h"

/**
 * Gegner mit einfacher, aber lebendiger KI:
 *  - betritt das Bild von der Seite
 *  - kreist/wartet auf Abstand, solange kein Angriffs-Token frei ist
 *  - greift nur an, wenn in Reichweite und auf gleicher Tiefe
 *  - Stil-Spezialitaeten: Skater-Rutschkick, Brecher-Sturmangriff, Boss-Wut
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerEnemy : public ABrawlerFighter
{
	GENERATED_BODY()

public:
	ABrawlerEnemy();

	/** Werte aus dem Profil uebernehmen (vor BeginPlay aufrufen) */
	void InitFromProfile(FName Type);
	static FEnemyProfile GetProfile(FName Type);

	const FEnemyProfile& GetEnemyProfile() const { return Profile; }
	bool IsBoss() const { return Profile.Style == EEnemyStyle::Boss; }

	void SetEntering(bool bInEntering);

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;
	virtual void TickControl(float DeltaSeconds) override;
	virtual void OnAttackFinished() override;
	virtual void OnHurt(ABrawlerFighter* Attacker, float Damage) override;
	virtual void OnDied() override;

private:
	FBrawlerAttack MakeMelee(bool bStrong) const;
	FBrawlerAttack MakeRush() const;
	void BeginEnemyAttack(const FBrawlerAttack& Attack);

	FEnemyProfile Profile;
	bool bEntering = false;
	float ThinkTimer = 0.f;
	float Cooldown = 1.f;
	float Side = 1.f;
	float DepthOffset = 0.f;
	float WaitDistance = 230.f;
	bool bHasToken = false;
	bool bEnraged = false;
};
