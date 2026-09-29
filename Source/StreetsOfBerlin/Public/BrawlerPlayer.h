#pragma once

#include "CoreMinimal.h"
#include "BrawlerFighter.h"
#include "BrawlerPlayer.generated.h"

/**
 * Spielfigur "Kai".
 *  - 4er-Combo (Jab, Gerade, Uppercut, Kick) – Kette laeuft nur weiter, wenn getroffen wird
 *  - Sprungkick, Rueckwaerts-Ellbogen
 *  - Spezialangriff (kostet rueckgewinnbare Energie, unverwundbar)
 *  - Griff durch Hineinlaufen: Knie x3 oder Wurf (Richtung weg + Angriff)
 *  - Gegenstaende aufheben (Angriff ueber einem Pickup)
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerPlayer : public ABrawlerFighter
{
	GENERATED_BODY()

public:
	ABrawlerPlayer();

	// --- Eingabe (vom PlayerController) -----------------------------------
	void SetMoveInput(const FVector2D& InMove) { MoveInput = InMove; }
	void PressAttack() { AttackBuffer = InputBufferTime; }
	void PressJump() { JumpBuffer = InputBufferTime; }
	void PressSpecial() { SpecialBuffer = InputBufferTime; }
	void PressBackAttack() { BackBuffer = InputBufferTime; }

	float GetRecoverableHealth() const { return RecoverableHealth; }

	void Celebrate();
	/** Nach Respawn: faellt ins Bild, Gegner in der Naehe werden umgeworfen */
	void DropIn();

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;
	virtual void TickControl(float DeltaSeconds) override;
	virtual void OnAttackHit(ABrawlerEntity* Target, const FBrawlerAttack& Attack) override;
	virtual void OnAttackFinished() override;
	virtual void OnHurt(ABrawlerFighter* Attacker, float Damage) override;
	virtual void OnDied() override;
	virtual void OnLanded() override;

private:
	void TickGroundControl(float DeltaSeconds);
	void TickGrabControl();
	bool TryPickup();
	bool TryGrab();
	void StartCombo(int32 Step);
	void StartSpecial();

	static const FBrawlerAttack& ComboAttack(int32 Step);
	static const FBrawlerAttack& JumpKickAttack();
	static const FBrawlerAttack& SpecialAttack();
	static const FBrawlerAttack& BackAttack();
	static const FBrawlerAttack& KneeAttack(bool bFinisher);
	static const FBrawlerAttack& ThrowAttack();

	FVector2D MoveInput = FVector2D::ZeroVector;
	float AttackBuffer = 0.f;
	float JumpBuffer = 0.f;
	float SpecialBuffer = 0.f;
	float BackBuffer = 0.f;
	static constexpr float InputBufferTime = 0.18f;

	int32 ComboStep = 0;
	bool bInComboAttack = false;
	bool bAttackFromGrab = false;
	bool bThrowReleased = false;
	bool bJumpAttackUsed = false;
	int32 KneeCount = 0;
	float GrabCooldown = 0.f;
	float WalkIntoTimer = 0.f;

	float RecoverableHealth = 0.f;
};
