#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BrawlerTypes.h"
#include "BrawlerEntity.generated.h"

class UPaperSpriteComponent;
class UPaperSprite;
class ABrawlerFighter;

/**
 * Basis fuer alles, was im Laufband existiert: Kaempfer, Props, Pickups, Effekte.
 * Verwaltet Belt-Scroll-Position, Sprite-Animation, Schatten und Sortierung.
 */
UCLASS(Abstract)
class STREETSOFBERLIN_API ABrawlerEntity : public AActor
{
	GENERATED_BODY()

public:
	ABrawlerEntity();

	virtual void Tick(float DeltaSeconds) override;

	// --- Belt-Scroll-Position ---------------------------------------------
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Brawler")
	float PosX = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Brawler")
	float Depth = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Brawler")
	float Height = 0.f;

	float VelX = 0.f;
	float VelDepth = 0.f;
	float VelZ = 0.f;

	/** +1 = schaut nach rechts, -1 = nach links */
	float Facing = 1.f;

	void SetBeltPosition(float InX, float InDepth, float InHeight = 0.f);

	// --- Treffer ------------------------------------------------------------
	virtual bool IsHittable(EBrawlerTeam AttackerTeam) const { return false; }
	virtual bool ReceiveHit(ABrawlerFighter* Attacker, const FBrawlerAttack& Attack, float Direction) { return false; }
	virtual float GetHurtHalfWidth() const { return Brawler::BodyHalfWidth; }
	virtual float GetHurtHeight() const { return Brawler::BodyHeight; }

	/** Hitstop: friert die Figur kurz ein (Trefferwucht) */
	void AddHitstop(float Seconds) { HitstopTimer = FMath::Max(HitstopTimer, Seconds); }
	bool IsInHitstop() const { return HitstopTimer > 0.f; }

	// --- Animation ----------------------------------------------------------
	/** Spielt Frames <Folder>/<Prefix>_NN ab */
	void PlayFrames(const FString& Folder, const FString& Prefix, float FPS, bool bLoop, bool bRestart = false);
	void SetStaticSprite(UPaperSprite* Sprite);

	int32 GetAnimFrame() const { return AnimFrame; }
	int32 GetAnimFrameCount() const { return CurrentFrames.Num(); }
	bool IsAnimFinished() const { return bAnimFinished; }
	const FString& GetAnimKey() const { return AnimKey; }
	void SetAnimFrame(int32 Frame);
	void SetAnimFPS(float FPS) { AnimFPS = FPS; }

protected:
	virtual void BeginPlay() override;

	/** Spiellogik pro Frame (wird waehrend Hitstop nicht aufgerufen) */
	virtual void TickEntity(float DeltaSeconds) {}

	void UpdateAnimation(float DeltaSeconds);
	void UpdateRender();

	UPROPERTY(VisibleAnywhere, Category = "Brawler")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "Brawler")
	TObjectPtr<UPaperSpriteComponent> Sprite;

	UPROPERTY(VisibleAnywhere, Category = "Brawler")
	TObjectPtr<UPaperSpriteComponent> Shadow;

	UPROPERTY()
	TArray<TObjectPtr<UPaperSprite>> CurrentFrames;

	/** Abstand Sprite-Mitte zu den Fuessen (Frame-Hoehe/2 - Fussabstand zum unteren Rand) */
	float SpriteFootOffset = Brawler::CharFrameSize * 0.5f - (Brawler::CharFrameSize - Brawler::CharFootY);
	float SpriteScale = 1.f;
	float ShadowScale = 1.f;
	int32 SortOffset = 0;
	bool bUseDepthSort = true;
	int32 FixedSortPriority = 0;
	/** Blinken (Unverwundbarkeit / Verschwinden) */
	float BlinkTimer = 0.f;
	float ShakeTimer = 0.f;

	float HitstopTimer = 0.f;

	FString AnimKey;
	float AnimTime = 0.f;
	float AnimFPS = 10.f;
	int32 AnimFrame = 0;
	bool bAnimLoop = true;
	bool bAnimFinished = false;
};
